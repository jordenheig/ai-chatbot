"""Pydantic schemas for document-related operations.

This module defines the data models for:
- Document metadata
- Processing status
- Document chunks
- API requests/responses
"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List

class ProcessingStatus(str, Enum):
    """Document processing status enumeration.
    
    Values:
        PENDING: Document is queued for processing
        PROCESSING: Document is being processed
        COMPLETED: Processing finished successfully
        FAILED: Processing encountered an error
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentBase(BaseModel):
    """Base document schema with common attributes."""
    filename: str = Field(..., description="Original filename")
    safe_name: str = Field(..., description="Sanitized filename for storage")
    content_type: str = Field(..., description="MIME type of the document")
    file_size: int = Field(..., description="Size in bytes")
    status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Current processing status"
    )

class DocumentCreate(DocumentBase):
    """Schema for document creation requests."""
    pass

class Document(DocumentBase):
    """Complete document schema with all attributes.
    
    Includes database-generated fields and relationships.
    """
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True 