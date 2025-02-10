from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentBase(BaseModel):
    filename: str
    safe_name: str
    content_type: str
    file_size: int
    status: ProcessingStatus

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True 