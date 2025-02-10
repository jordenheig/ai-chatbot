from typing import BinaryIO, List
from any_parser import AnyParser
from app.db.models import Document, ProcessingStatus
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import store_document_chunks
from sqlalchemy.orm import Session
from app.core.logging import logger
from celery import Task

class DocumentProcessor:
    def __init__(self):
        self.parser = AnyParser()
    
    async def process_document(self, file_content: bytes, filename: str) -> List[str]:
        """Process document content and return chunks of text"""
        try:
            # Parse document using AnyParser
            parsed_content = self.parser.parse(file_content, filename)
            
            # Extract text content
            text_content = parsed_content.text
            
            # Split into chunks (implement your chunking strategy)
            chunks = self._split_into_chunks(text_content)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise
    
    def _split_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Adjust chunk end to not split words
            if end < text_length:
                # Find the last space before chunk_size
                while end > start and text[end] != ' ':
                    end -= 1
            
            # Add chunk
            chunks.append(text[start:end].strip())
            
            # Move start position for next chunk, considering overlap
            start = end - overlap
        
        return chunks

# Create Celery task for document processing
class DocumentProcessingTask(Task):
    _processor = None
    
    @property
    def processor(self) -> DocumentProcessor:
        if self._processor is None:
            self._processor = DocumentProcessor()
        return self._processor

@celery_app.task(base=DocumentProcessingTask)
async def process_document_task(document_id: int, file_content: bytes):
    """Celery task to process documents asynchronously"""
    try:
        # Get document from database
        db = SessionLocal()
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        # Update status to processing
        document.status = ProcessingStatus.PROCESSING
        db.commit()
        
        # Process document
        chunks = await process_document.processor.process_document(
            file_content,
            document.filename
        )
        
        # Generate embeddings for chunks
        embeddings = await generate_embeddings(chunks)
        
        # Store chunks and embeddings in vector store
        await store_document_chunks(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings
        )
        
        # Update document status to completed
        document.status = ProcessingStatus.COMPLETED
        db.commit()
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        document.status = ProcessingStatus.FAILED
        db.commit()
        raise
    
    finally:
        db.close() 