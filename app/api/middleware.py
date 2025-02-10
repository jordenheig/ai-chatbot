"""Middleware for the FastAPI application.

Provides:
- Request ID tracking
- Request logging
- Error handling
- Performance monitoring
"""

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and adding request IDs."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to logging context
        logger_adapter = logging.LoggerAdapter(
            logger,
            {'request_id': request_id}
        )
        
        # Log request
        start_time = time.time()
        logger_adapter.info(
            "Request started",
            extra={
                'method': request.method,
                'url': str(request.url),
                'client_host': request.client.host if request.client else None,
                'request_id': request_id
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger_adapter.info(
                "Request completed",
                extra={
                    'status_code': response.status_code,
                    'process_time': process_time,
                    'request_id': request_id
                }
            )
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger_adapter.error(
                "Request failed",
                extra={
                    'error': str(e),
                    'process_time': process_time,
                    'request_id': request_id
                },
                exc_info=True
            )
            raise 