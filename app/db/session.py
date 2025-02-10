"""Database session management for the RAG Chatbot.

This module handles database connection and session management,
including connection pooling and retry logic for resilient database
operations.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import time
import logging

logger = logging.getLogger(__name__)

def get_engine():
    """Create database engine with retry logic.
    
    Returns:
        SQLAlchemy engine instance
        
    Raises:
        Exception: If database connection fails after maximum retries
    """
    max_retries = 5
    retry_interval = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(
                settings.SQLALCHEMY_DATABASE_URI,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args={"connect_timeout": 5}
            )
            # Test the connection
            engine.connect()
            return engine
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error("Failed to connect to database after maximum retries")
                raise

# Create engine and session factory
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session with automatic cleanup.
    
    Yields:
        SQLAlchemy session
        
    Note:
        This function is designed to be used as a FastAPI dependency
        to ensure proper session cleanup after request handling.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 