"""Database models for the RAG Chatbot application.

This module defines SQLAlchemy ORM models for:
- Users and authentication
- Documents and their processing status
- Chat sessions and messages
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class ProcessingStatus(enum.Enum):
    """Document processing status enumeration.
    
    Attributes:
        PENDING: Document is queued for processing
        PROCESSING: Document is currently being processed
        COMPLETED: Document processing completed successfully
        FAILED: Document processing failed
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    """User model for authentication and ownership.
    
    Attributes:
        id: Unique identifier
        email: User's email address (used for login)
        hashed_password: Securely hashed password
        documents: List of documents owned by the user
        chat_sessions: List of chat sessions belonging to the user
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    documents = relationship("Document", back_populates="owner")
    chat_sessions = relationship("ChatSession", back_populates="user")

class Document(Base):
    """Document model for storing uploaded file metadata.
    
    Attributes:
        id: Unique identifier
        filename: Original filename
        safe_name: Sanitized filename for storage
        content_type: MIME type
        file_size: Size in bytes
        status: Current processing status
        created_at: Upload timestamp
        updated_at: Last update timestamp
        owner_id: Reference to user who uploaded
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)  # Original filename
    safe_name = Column(String, nullable=False)  # Sanitized filename for storage
    content_type = Column(String)  # MIME type
    file_size = Column(Integer, nullable=False)  # Size in bytes
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class ChatSession(Base):
    """Chat session model for organizing conversations.
    
    Attributes:
        id: Unique identifier
        title: Session title
        user_id: ID of the session owner
        user: Reference to the session owner
        messages: List of messages in the session
        created_at: Timestamp of session creation
    """
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    """Chat message model for storing conversation history.
    
    Attributes:
        id: Unique identifier
        session_id: ID of the parent chat session
        role: Message role (user/assistant)
        content: Message content
        created_at: Timestamp of message creation
        session: Reference to the parent chat session
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ChatSession", back_populates="messages") 