from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.models import Document, ProcessingStatus
from app.core.security import get_current_user
from app.services.document_processor import process_document
from app.db.repositories import DocumentRepository
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
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