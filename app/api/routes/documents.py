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

router = APIRouter()

@router.get("/status-stream")
async def status_stream(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EventSourceResponse:
    """Stream document status updates using Server-Sent Events."""
    
    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            # Get all user's documents
            documents = (
                db.query(Document)
                .filter(Document.owner_id == current_user.id)
                .all()
            )
            
            # Send status updates
            data = [{
                "id": doc.id,
                "status": doc.status.value,
                "filename": doc.filename
            } for doc in documents]
            
            yield json.dumps({"data": data})
            
            # Wait before next update
            await asyncio.sleep(2)
    
    return EventSourceResponse(event_generator())

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    callback_url: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create document record
    document = Document(
        filename=file.filename,
        content_type=file.content_type,
        status=ProcessingStatus.PENDING,
        owner_id=current_user.id
    )
    db.add(document)
    db.commit()
    
    # Queue document processing task
    process_document.delay(document.id, await file.read())
    
    # Send status update to callback URL
    async with httpx.AsyncClient() as client:
        await client.post(callback_url, json={"status": document.status.value})
    
    return {"document_id": document.id, "status": "pending"}

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