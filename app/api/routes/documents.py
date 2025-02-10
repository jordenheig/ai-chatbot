from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from typing import List, AsyncGenerator
import asyncio
import json
from app.db.models import Document, ProcessingStatus
from app.core.security import get_current_user
from app.services.document_processor import process_document
from app.db.repositories import DocumentRepository
from app.api.dependencies import get_db
import httpx
import os
from pathlib import Path
from datetime import datetime

router = APIRouter()

@router.get("/status-stream")
async def status_stream(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EventSourceResponse:
    """Stream document status updates using Server-Sent Events."""
    
    async def event_generator():
        while True:
            # Get all user's documents with metadata
            documents = (
                db.query(Document)
                .filter(Document.owner_id == current_user.id)
                .all()
            )
            
            # Send status updates with full metadata
            data = [{
                "id": doc.id,
                "filename": doc.filename,
                "safe_name": doc.safe_name,
                "content_type": doc.content_type,
                "file_size": doc.file_size,
                "status": doc.status.value,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            } for doc in documents]
            
            yield json.dumps({"data": data})
            await asyncio.sleep(2)
    
    return EventSourceResponse(event_generator())

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document for processing.
    
    Stores document metadata and queues processing task.
    """
    try:
        # Get file size
        file_content = await file.read()
        file_size = len(file_content)
        
        # Create safe filename
        original_filename = file.filename
        safe_name = Path(original_filename).stem + "_" + str(int(datetime.utcnow().timestamp())) + Path(original_filename).suffix
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
        
        # Create document record
        document = Document(
            filename=original_filename,
            safe_name=safe_name,
            content_type=file.content_type,
            file_size=file_size,
            status=ProcessingStatus.PENDING,
            owner_id=current_user.id
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Queue processing task
        process_document.delay(document.id, file_content)
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "safe_name": document.safe_name,
            "size": document.file_size,
            "status": document.status.value,
            "created_at": document.created_at
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/status/{document_id}")
async def get_document_status(
    document_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = DocumentRepository(db).get_document(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"status": document.status.value}

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = DocumentRepository(db).get_document(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(document)
    db.commit()
    return {"status": "success"} 