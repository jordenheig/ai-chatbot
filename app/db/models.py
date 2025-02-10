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
    """Document model for storing uploaded files.
    
    Attributes:
        id: Unique identifier
        filename: Original filename
        content_type: MIME type of the document
        status: Current processing status
        owner_id: ID of the user who uploaded the document
        owner: Reference to the user who owns the document
        created_at: Timestamp of document creation
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    content_type = Column(String)
    status = Column(Enum(ProcessingStatus))
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", back_populates="documents")

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