"""Document processing service for the RAG Chatbot.

This module handles:
- Document text extraction
- OCR processing for images
- Text chunking and embedding
- Vector store integration
- Processing status management
"""

from typing import BinaryIO, List, Dict, Tuple
from any_parser import AnyParser
from app.db.models import Document, ProcessingStatus
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import store_document_chunks
from sqlalchemy.orm import Session
from app.core.logging import logger
from celery import Task
import fitz  # PyMuPDF
import easyocr
import io
from PIL import Image
import numpy as np
from app.api.connection_manager import ConnectionManager
from datetime import datetime, timedelta

class DocumentProcessor:
    """Handles document processing pipeline.
    
    This class manages:
    - Text extraction from various formats
    - OCR for images and scanned documents
    - Text chunking for vector storage
    - Processing status updates
    """
    
    def __init__(self):
        """Initialize document processor with required components."""
        self.parser = AnyParser()
        # Initialize EasyOCR reader (only initialize once for performance)
        self.ocr_reader = easyocr.Reader(['en'])
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
    async def process_document(self, document_id: int, content: bytes) -> None:
        """Process a document through the complete pipeline.
        
        Args:
            document_id: ID of document to process
            content: Raw document content
            
        Raises:
            ProcessingError: If document processing fails
        """
        try:
            # Parse document using AnyParser
            parsed_content = self.parser.parse(content, document.filename)
            text_content = parsed_content.text
            
            # Special handling for PDFs with images
            if document.filename.lower().endswith('.pdf'):
                text_by_page = self._split_text_by_pages(text_content)
                ocr_by_page = await self._process_pdf_images(content)
                merged_text = self._merge_text_and_ocr(text_by_page, ocr_by_page)
                text_content = merged_text
            
            chunks = self._split_into_chunks(text_content)
            
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
            
            # Send real-time update
            await manager.send_document_update(
                document.owner_id,
                document_id,
                ProcessingStatus.COMPLETED.value
            )
            
            logger.info(
                "Document processing completed",
                extra={
                    'document_id': document_id,
                    'chunks_count': len(chunks),
                    'embeddings_count': len(embeddings)
                }
            )
        except Exception as e:
            logger.error(
                "Document processing failed",
                extra={
                    'document_id': document_id,
                    'error': str(e)
                },
                exc_info=True
            )
        finally:
            db.close()

    def _split_text_by_pages(self, text: str) -> Dict[int, str]:
        """Split document text into pages based on page markers.
        
        Args:
            text: Full document text
            
        Returns:
            Dictionary mapping page numbers to text content
        """
        pages = {}
        current_page = 1
        current_text = []
        
        for line in text.split('\n'):
            # You might need to adjust this based on how your parser indicates page breaks
            if line.strip().startswith('Page ') or line.strip().startswith('[Page '):
                if current_text:
                    pages[current_page] = '\n'.join(current_text)
                    current_text = []
                current_page += 1
            else:
                current_text.append(line)
        
        # Add the last page
        if current_text:
            pages[current_page] = '\n'.join(current_text)
        
        return pages
    
    async def _process_pdf_images(self, file_content: bytes) -> Dict[int, List[Tuple[float, str]]]:
        """Extract and process images from PDF, maintaining page and position order.
        
        Args:
            file_content: Raw PDF file bytes
            
        Returns:
            Dictionary mapping page numbers to lists of (position, text) tuples
        """
        try:
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            extracted_texts_by_page = {}
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                page_texts = []
                
                # Get images from page
                image_list = page.get_images(full=True)
                
                for img_index, img_info in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img_info[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Get image position on page
                        image_rect = page.get_image_bbox(xref)
                        y_position = image_rect.y0  # Vertical position for ordering
                        
                        # Convert to PIL Image
                        image = Image.open(io.BytesIO(image_bytes))
                        
                        # Convert to RGB if necessary
                        if image.mode != 'RGB':
                            image = image.convert('RGB')
                        
                        # Convert to numpy array for EasyOCR
                        image_np = np.array(image)
                        
                        # Perform OCR
                        results = self.ocr_reader.readtext(image_np)
                        
                        # Extract text from results
                        if results:
                            text = " ".join([text[1] for text in results])
                            page_texts.append((y_position, text))
                            
                    except Exception as e:
                        logger.warning(f"Error processing image {img_index} on page {page_num + 1}: {str(e)}")
                        continue
                
                if page_texts:
                    # Sort texts by vertical position
                    page_texts.sort(key=lambda x: x[0])
                    extracted_texts_by_page[page_num + 1] = page_texts
            
            pdf_document.close()
            return extracted_texts_by_page
            
        except Exception as e:
            logger.error(f"Error processing PDF images: {str(e)}")
            return {}
    
    def _merge_text_and_ocr(
        self,
        text_by_page: Dict[int, str],
        ocr_by_page: Dict[int, List[Tuple[float, str]]]
    ) -> str:
        """Merge regular text and OCR text while maintaining document structure.
        
        Args:
            text_by_page: Dictionary of page numbers to regular text
            ocr_by_page: Dictionary of page numbers to OCR text with positions
            
        Returns:
            Merged text content with page breaks
        """
        merged_pages = []
        
        # Get all page numbers
        all_pages = sorted(set(list(text_by_page.keys()) + list(ocr_by_page.keys())))
        
        for page_num in all_pages:
            page_content = []
            
            # Add regular text if exists
            if page_num in text_by_page:
                page_content.append(text_by_page[page_num])
            
            # Add OCR text if exists
            if page_num in ocr_by_page:
                # Only add the text part from the (position, text) tuples
                ocr_texts = [text for _, text in ocr_by_page[page_num]]
                if ocr_texts:
                    page_content.append("\n".join(ocr_texts))
            
            # Join page content with newlines
            if page_content:
                merged_pages.append("\n".join(page_content))
        
        # Join all pages with page separators
        return "\n\n=== Page Break ===\n\n".join(merged_pages)
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks for vector storage.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            # Adjust chunk end to not split words
            if end < text_length:
                # Find the last space before chunk_size
                while end > start and text[end] != ' ':
                    end -= 1
            
            # Add chunk
            chunks.append(text[start:end].strip())
            
            # Move start position for next chunk
            start = end - self.chunk_overlap
        
        return chunks

# Create Celery task for document processing
class DocumentProcessingTask(Task):
    _processor = None
    
    @property
    def processor(self) -> DocumentProcessor:
        if self._processor is None:
            self._processor = DocumentProcessor()
        return self._processor

@celery_app.task(
    bind=True,
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
async def process_document_task(self, document_id: int, file_content: bytes):
    """Celery task to process documents asynchronously with retries."""
    try:
        logger.info(
            "Starting document processing",
            extra={
                'document_id': document_id,
                'filename': document.filename,
                'content_type': document.content_type
            }
        )
        # Get document from database
        db = SessionLocal()
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        # Update status to processing
        document.status = ProcessingStatus.PROCESSING
        db.commit()
        
        # Send real-time update
        await manager.send_document_update(
            document.owner_id, 
            document_id, 
            ProcessingStatus.PROCESSING.value
        )
        
        # Process document
        await process_document.processor.process_document(
            document_id,
            file_content
        )
        
        logger.info(
            "Document processing completed",
            extra={
                'document_id': document_id,
                'chunks_count': len(chunks),
                'embeddings_count': len(embeddings)
            }
        )
    except Exception as e:
        logger.error(
            "Document processing failed",
            extra={
                'document_id': document_id,
                'error': str(e),
                'retry_count': self.request.retries
            },
            exc_info=True
        )
    finally:
        db.close() 

@celery_app.task
async def cleanup_old_documents():
    """Periodic task to clean up old or failed documents."""
    try:
        db = SessionLocal()
        # Find old failed documents (older than 7 days)
        old_docs = (
            db.query(Document)
            .filter(
                Document.status == ProcessingStatus.FAILED,
                Document.created_at < datetime.utcnow() - timedelta(days=7)
            )
            .all()
        )
        
        for doc in old_docs:
            # Delete from vector store
            await vector_store.delete_document(doc.id)
            # Delete from database
            db.delete(doc)
        
        db.commit()
        logger.info(f"Cleaned up {len(old_docs)} old documents")
        
    except Exception as e:
        logger.error(f"Error cleaning up old documents: {str(e)}")
        raise
    finally:
        db.close() 