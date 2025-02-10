"""Celery worker configuration for background tasks.

This module configures Celery for handling:
- Document processing tasks
- Vector store maintenance
- Periodic cleanup tasks
- Task routing and scheduling
"""

from celery import Celery
from app.core.config import settings
from app.core.logging import logger

celery_app = Celery(
    "worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=[
        "app.services.document_processor",
        "app.services.vector_store"
    ]
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_routes={
        "app.services.document_processor.*": {"queue": "document_processing"},
        "app.services.vector_store.*": {"queue": "vector_store"},
    }
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-documents": {
        "task": "app.services.document_processor.cleanup_old_documents",
        "schedule": 86400.0,  # 24 hours
        "options": {"queue": "document_processing"}
    },
    "optimize-vector-index": {
        "task": "app.services.vector_store.optimize_index",
        "schedule": 43200.0,  # 12 hours
        "options": {"queue": "vector_store"}
    }
}

@celery_app.task(bind=True)
def test_task(self):
    """Test task to verify Celery configuration.
    
    Returns:
        Dict containing task status and worker info
    """
    try:
        return {
            "status": "success",
            "message": "Celery worker is functioning correctly",
            "worker_id": self.request.id
        }
    except Exception as e:
        logger.error(f"Test task failed: {str(e)}")
        raise 