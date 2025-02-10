from celery import shared_task
from app.services.document_processor import process_document_task
from app.core.logging import logger

@shared_task(bind=True)
def process_uploaded_document(self, document_id: int, file_content: bytes):
    try:
        return process_document_task(document_id, file_content)
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        self.retry(exc=e, countdown=60)  # Retry after 60 seconds 