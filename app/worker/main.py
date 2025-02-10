"""Celery worker configuration for background tasks.

This module configures Celery for handling background tasks such as:
- Document processing and OCR
- Vector index management
- Periodic cleanup tasks
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=[
        "app.services.document_processor",
        "app.services.vector_store"
    ]
)

# Configure Celery
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

# Optional: Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-documents": {
        "task": "app.services.document_processor.cleanup_old_documents",
        "schedule": 86400.0,  # 24 hours
    },
    "optimize-vector-index": {
        "task": "app.services.vector_store.optimize_index",
        "schedule": 43200.0,  # 12 hours
    }
} 